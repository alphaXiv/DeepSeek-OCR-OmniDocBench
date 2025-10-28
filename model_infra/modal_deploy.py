
from model_infra.modal_app_async import app

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "deploy":
        print("Deploying to Modal...")
        app.deploy()
    else:
        print("Run 'python model_infra/modal_deploy.py deploy' to deploy to Modal")
