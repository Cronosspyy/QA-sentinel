import boto3

def list_models():
    bedrock = boto3.client(service_name='bedrock', region_name='us-west-2')
    
    try:
        response = bedrock.list_foundation_models(
            byProvider='amazon',
            byOutputModality='TEXT'
        )
        
        print("Available Amazon Text Models:")
        for model in response['modelSummaries']:
            print(f"- {model['modelId']} ({model['modelName']})")
            
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
