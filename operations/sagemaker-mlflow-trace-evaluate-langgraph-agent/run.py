from utils import run_evaluation_mlflow, register_agent

def main():
    print("Evaluate agentops-traceevaluate-langgraph-mlflow!")
    
    # Export all results to sagemaker MLFlow tracking server
    # Evaluation using only MLFlow
    run_evaluation_mlflow()
    #register_agent("graph.py")


if __name__ == "__main__":
    main()
