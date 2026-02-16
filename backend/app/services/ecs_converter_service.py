"""
ECS Fargate document conversion service.
Uploads to S3, runs ECS task, waits for completion, downloads result.
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Optional

import boto3

from app.core.config import settings
from app.utils.base_converter import ConversionError


def _get_network_config():
    """Get VPC/subnet/SG from instance metadata or config."""
    subnet = getattr(settings, "ECS_SUBNET_ID", None)
    sg = getattr(settings, "ECS_SECURITY_GROUP_ID", None)
    if subnet and sg:
        return subnet, sg
    try:
        import urllib.request
        token_url = "http://169.254.169.254/latest/api/token"
        req = urllib.request.Request(token_url, method="PUT", headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"})
        with urllib.request.urlopen(req, timeout=2) as r:
            token = r.read().decode()
        base = "http://169.254.169.254/latest/meta-data/network/interfaces/macs/"
        mac_req = urllib.request.Request(base, headers={"X-aws-ec2-metadata-token": token})
        with urllib.request.urlopen(mac_req, timeout=2) as r:
            macs = r.read().decode().strip().split("\n")
        if macs:
            mac = macs[0].rstrip("/")
            with urllib.request.urlopen(
                urllib.request.Request(f"{base}{mac}subnet-id", headers={"X-aws-ec2-metadata-token": token}),
                timeout=2,
            ) as r:
                subnet = r.read().decode().strip()
            with urllib.request.urlopen(
                urllib.request.Request(f"{base}{mac}security-group-ids", headers={"X-aws-ec2-metadata-token": token}),
                timeout=2,
            ) as r:
                sg = r.read().decode().strip().split("\n")[0]
            return subnet, sg
    except Exception:
        pass
    raise ConversionError("Could not get ECS network config (missing metadata or ECS_SUBNET_ID/ECS_SECURITY_GROUP_ID)")


def convert_via_ecs(
    input_path: str,
    output_path: str,
    source_format: str,
    target_format: str,
    input_bucket: Optional[str] = None,
    output_bucket: Optional[str] = None,
) -> bool:
    """
    Convert document using ECS Fargate task.
    Uploads input to S3, runs task, waits, downloads result.
    """
    region = getattr(settings, "AWS_REGION", "us-east-2")
    cluster = getattr(settings, "ECS_CLUSTER_NAME", "document-converter-cluster")
    task_def = getattr(settings, "ECS_TASK_FAMILY", "document-converter-task")
    account_id = getattr(settings, "AWS_ACCOUNT_ID", "766092484543")

    inp = getattr(settings, "ECS_INPUT_BUCKET", "") or ""
    out = getattr(settings, "ECS_OUTPUT_BUCKET", "") or ""
    input_bucket = input_bucket or inp or f"docai-converter-input-{account_id}"
    output_bucket = output_bucket or out or f"docai-converter-output-{account_id}"

    s3 = boto3.client("s3", region_name=region)
    ecs = boto3.client("ecs", region_name=region)

    input_key = f"uploads/{Path(input_path).name}"
    output_format = target_format.lower().replace(".", "")

    # 1. Upload to S3
    try:
        s3.upload_file(input_path, input_bucket, input_key)
    except Exception as e:
        raise ConversionError(f"Failed to upload to S3: {e}") from e

    subnet_id, sg_id = _get_network_config()
    event = json.dumps({"input_key": input_key, "output_format": output_format})
    overrides = {
        "containerOverrides": [
            {"name": "document-converter", "command": ["python3", "converter.py", event]}
        ]
    }
    network_config = {
        "awsvpcConfiguration": {
            "subnets": [subnet_id],
            "securityGroups": [sg_id],
            "assignPublicIp": "ENABLED",
        }
    }

    # 2. Run ECS task
    try:
        resp = ecs.run_task(
            cluster=cluster,
            taskDefinition=task_def,
            launchType="FARGATE",
            networkConfiguration=network_config,
            overrides=overrides,
        )
        tasks = resp.get("tasks", [])
        failures = resp.get("failures", [])
        if failures:
            raise ConversionError(f"ECS run_task failed: {failures[0].get('reason', failures)}")
        if not tasks:
            raise ConversionError("ECS run_task returned no tasks")
        task_arn = tasks[0]["taskArn"]
    except ConversionError:
        raise
    except Exception as e:
        raise ConversionError(f"Failed to run ECS task: {e}") from e

    # 3. Poll until stopped (max ~5 min)
    max_wait = 300
    poll_interval = 3
    elapsed = 0
    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval
        desc = ecs.describe_tasks(cluster=cluster, tasks=[task_arn])
        task = desc["tasks"][0]
        status = task["lastStatus"]
        if status == "STOPPED":
            stop_code = task.get("stopCode", "")
            if stop_code == "EssentialContainerExited":
                exit_code = task.get("containers", [{}])[0].get("exitCode", -1)
                if exit_code != 0:
                    raise ConversionError(f"ECS container exited with code {exit_code}")
            break
        if status == "DEPROVISIONING":
            break
    else:
        raise ConversionError("ECS task did not complete within timeout")

    # 4. Download result from S3
    output_key = f"converted/{Path(input_path).stem}.{output_format}"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        s3.download_file(output_bucket, output_key, output_path)
    except Exception as e:
        raise ConversionError(f"Failed to download result from S3: {e}") from e

    return True
