/**
 * PM2 ecosystem file - Migración Amazon Linux 2023
 * Uso: pm2 start ecosystem.config.cjs
 *      pm2 start ecosystem.config.cjs --only backend
 *      pm2 save && pm2 startup  # persistir tras reinicio
 */

module.exports = {
  apps: [
    {
      name: 'backend',
      cwd: '/home/ec2-user/backend',
      script: '/home/ec2-user/.venv-new/bin/python',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 5000',
      interpreter: 'none',
      env: { NODE_ENV: 'production' },
      error_file: '/home/ec2-user/logs/backend-err.log',
      out_file: '/home/ec2-user/logs/backend-out.log',
      merge_logs: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
    },
    {
      name: 'backend-collab',
      cwd: '/home/ec2-user/backend-collab',
      script: 'node',
      args: 'dist/server.js',
      interpreter: 'none',
      env: { PORT: 3001 },
      error_file: '/home/ec2-user/logs/collab-err.log',
      out_file: '/home/ec2-user/logs/collab-out.log',
      merge_logs: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
    },
    {
      name: 'frontend',
      cwd: '/home/ec2-user/frontend',
      script: 'npm',
      args: 'run dev',
      interpreter: 'none',
      env: { NODE_ENV: 'development' },
      error_file: '/home/ec2-user/logs/frontend-err.log',
      out_file: '/home/ec2-user/logs/frontend-out.log',
      merge_logs: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
    },
  ],
};
