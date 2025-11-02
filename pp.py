import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError

class BedrockConnector:
    def __init__(self, region_name='eu-central-1'):
        """
        Initialize Bedrock client
        """
        self.region_name = region_name
        self.client = self._create_client()
    
    def _create_client(self):
        """Create Bedrock runtime client"""
        try:
            client = boto3.client(
                'bedrock-runtime',
                region_name=self.region_name
            )
            print("✅ Bedrock client created successfully")
            return client
        except NoCredentialsError:
            print("❌ AWS credentials not found")
            raise
        except Exception as e:
            print(f"❌ Error creating Bedrock client: {e}")
            raise
    
    def list_foundation_models(self):
        """List available foundation models"""
        try:
            print(f"Region : ", self.region_name )
            bedrock_client = boto3.client('bedrock', region_name=self.region_name)
            response = bedrock_client.list_foundation_models()
            
            print("Available Foundation Models:")
            print("-" * 50)
            
            for model in response.get('modelSummaries', []):
                print(f"Model ID: {model['modelId']}")
                print(f"Model Name: {model['modelName']}")
                print(f"Provider: {model.get('providerName', 'N/A')}")
                print(f"Input Modalities: {model.get('inputModalities', [])}")
                print(f"Output Modalities: {model.get('outputModalities', [])}")
                print("-" * 30)
                
            return response
            
        except ClientError as e:
            print(f"Error listing models: {e}")
            return None
    
    def invoke_model(self, model_id, prompt, **kwargs):
        """
        Invoke a Bedrock model
        
        Args:
            model_id (str): Model ID (e.g., 'anthropic.claude-v2')
            prompt (str): Input prompt
            **kwargs: Additional parameters for the model
        
        Returns:
            dict: Model response
        """
        try:
            # Different models have different request formats
            if 'anthropic.claude' in model_id:
                body = self._create_anthropic_body(prompt, **kwargs)
                content_type = 'application/json'
                accept = 'application/json'
                
            elif 'amazon.titan' in model_id:
                body = self._create_titan_body(prompt, **kwargs)
                content_type = 'application/json'
                accept = 'application/json'
                
            elif 'ai21.j2' in model_id:
                body = self._create_ai21_body(prompt, **kwargs)
                content_type = 'application/json'
                accept = 'application/json'
                
            else:
                raise ValueError(f"Unsupported model: {model_id}")
            
            # Invoke the model
            response = self.client.invoke_model(
                modelId=model_id,
                body=body,
                contentType=content_type,
                accept=accept
            )
            
            # Parse response based on model type
            if 'anthropic.claude' in model_id:
                return self._parse_anthropic_response(response)
            elif 'amazon.titan' in model_id:
                return self._parse_titan_response(response)
            elif 'ai21.j2' in model_id:
                return self._parse_ai21_response(response)
                
        except ClientError as e:
            print(f"❌ Error invoking model: {e}")
            return None
    
    def _create_anthropic_body(self, prompt, max_tokens=1000, temperature=0.5):
        """Create request body for Anthropic models"""
        return json.dumps({
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": max_tokens,
            "temperature": temperature,
            "stop_sequences": ["\n\nHuman:"]
        })
    
    def _create_titan_body(self, prompt, max_tokens=1000, temperature=0.5):
        """Create request body for Amazon Titan models"""
        return json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": 0.9
            }
        })
    
    def _create_ai21_body(self, prompt, max_tokens=1000, temperature=0.5):
        """Create request body for AI21 Jurassic models"""
        return json.dumps({
            "prompt": prompt,
            "maxTokens": max_tokens,
            "temperature": temperature,
            "topP": 0.9
        })
    
    def _parse_anthropic_response(self, response):
        """Parse Anthropic model response"""
        response_body = json.loads(response['body'].read())
        return response_body.get('completion', 'No response')
    
    def _parse_titan_response(self, response):
        """Parse Titan model response"""
        response_body = json.loads(response['body'].read())
        return response_body['results'][0]['outputText']
    
    def _parse_ai21_response(self, response):
        """Parse AI21 model response"""
        response_body = json.loads(response['body'].read())
        return response_body['completions'][0]['data']['text']

# SNS Message
def send_sns_message(topic_arn, message, region='eu-central-1'):
    """
    Send a message to an SNS topic

    Args:
        topic_arn (str): The ARN of the SNS topic
        message (str): The message to send
        region (str): AWS region
    """
    try:
        # Create SNS client
        sns = boto3.client('sns', region_name=region)

        # Send message
        response = sns.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject='SNS Notification'  # Optional subject
        )

        print(f"Message sent successfully! Message ID: {response['MessageId']}")
        return response

    except Exception as e:
        print(f"Error sending message: {e}")
        return None

# Example usage
def main():
    try:
    

        # Initialize Bedrock connector
        bedrock = BedrockConnector(region_name='eu-central-1')
        
        # List available models
        print("📋 Listing available models...")
        bedrock.list_foundation_models()
        
        # Example prompt
        prompt = "Explain quantum computing in simple terms."
        
        # Invoke Claude model
        print(f"\n Invoking Claude model with prompt: '{prompt}'")
        response = bedrock.invoke_model(
            model_id='amazon.titan-text-express-v1',
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )
        
        print("\n Model Response:")
        print(response)
        
        # Invoke Titan model (alternative example)
        print(f"\n Invoking Titan model...")
        titan_response = bedrock.invoke_model(
            model_id='amazon.titan-text-express-v1',
            prompt="Write a short poem about AI",
            max_tokens=200,
            temperature=0.8
        )
        
        print("\nTitan Response:")
        print(titan_response)
        send_sns_message( "arn:aws:sns:eu-central-1:346430704880:myNotify" ,titan_response, "eu-central-1")

    except Exception as e:
        print(f" Error in main: {e}")

if __name__ == "__main__":
    main()

