# PROMPT PENDIENTE - Document Converter AWS (<1000 chars)

```
Completar DocAI doc-converter(i-0fb5d6c4f09cb51eb,us-east-2).1)Crear policy:aws iam create-policy --policy-name DocumentConverterDeployPolicy --policy-document file://~/document-converter/iam-policy.json 2)Adjuntar al rol:aws iam attach-role-policy --role-name EC2-SessionManager-Role --policy-arn arn:aws:iam::766092484543:policy/DocumentConverterDeployPolicy 3)Deploy:cd ~/document-converter;./scripts/deploy.sh;./scripts/setup-ecs.sh;./scripts/test-conversion.sh Alt:CloudShell us-east-2 si sin permiso IAM
```
