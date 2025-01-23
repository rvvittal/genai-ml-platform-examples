
# SageMaker Inference Component Scale-to-zero CDK

A project that deploys Llama 3 8b on an Amazon SageMaker Inference Component that scales to 0 with no traffic and scale up when invocations start coming in.


Once the stack is deployed, after some time the Inference Component will scale to zero which will cause errors when invoking the model. The Inference Component may take a few minutes to scale after receiving unsuccessful invocations after which invocations will succeed.

This stack is currently configured to use us-east-1 with the ECR image URI. You can configure the ECR URI by modifying the parameter when deploying:
```
cdk deploy --parameters ECRImage=<ECR URI>
```

The `cdk.json` file tells the CDK Toolkit how to execute your app.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
