resource "aws_iam_role" "lambda_iam_role" {
  name = "{{inputs.lambda_role}}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    },
    {
        "Action": ["rds:DeleteDBSnapshot", "rds:DeleteDBClusterSnapshot", "rds:CreateDBSnapshot", "rds:CreateDBClusterSnapshot"],
        "Effect": "Allow",
        "Resource: "*"
    }
  ]
}
EOF
}


# Para o deploy funcionar, gerar um arquivo .zip do arquivo main.py com o nome lambda_function.zip
resource "aws_lambda_function" "lambda_start_workflow" {
  filename      = "lambda_function.zip"
  function_name = "lambda_start_workflow"
  role          = aws_iam_role.lambda_iam_role.arn
  handler       = "main.lambda_handler"

  source_code_hash = filebase64sha256("lambda_function.zip")

  runtime = "python3.8"

  environment {
    variables = {
      WORKFLOW_NAME = {{inputs.workflow_name}}
      BUCKETS_DBS = {{inputs.bucket_name}}
    }
  }
}