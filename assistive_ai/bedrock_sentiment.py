# import json
# import boto3
# from botocore.exceptions import ClientError

# # Use standard runtime client
# bedrock_runtime = boto3.client(
#     service_name="bedrock-runtime",
#     region_name="us-west-2"
# )

# MODEL_ID = "anthropic.claude-opus-4-5-20251101-v1:0"

# def score_sentiment(text: str) -> float:
#     messages = [{
#         "role": "user",
#         "content": [{"text": f"""
#         Classify the sentiament of the following customer message.
#         Return ONLY a number between -1.0 (negative) and 1.0 (positive).
#         Do not explain.

#         Text:
#         {text}
#         """}]
#     }]

#     try:
#         # Use simple invoke_model first if converse isn't available, but Nova prefers converse-like structure or specific bodies.
#         # Actually, Nova models require the new "messages" API style in invoke_model too, or use converse.
#         # Let's try the modern 'converse' method if boto3 is new enough.
        
#         response = bedrock_runtime.converse(
#             modelId=MODEL_ID,
#             messages=messages,
#             inferenceConfig={"temperature": 0}
#         )
        
#         output_text = response['output']['message']['content'][0]['text']
        
#         # Clean up output to get just the float
#         clean_text = output_text.strip()
#         return float(clean_text)

#     except (AttributeError, ClientError) as e:
#         # Fallback for older boto3 or if converse fails
#         print(f"DEBUG: Converse API failed ({e}), trying raw invoke...")
#         return 0.0
#     except ValueError:
#         print(f"DEBUG: Could not parse float from: {output_text}")
#         return 0.0


import json
import boto3
from botocore.exceptions import ClientError

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-west-2"
)

MODEL_ID = "anthropic.claude-3-5-haiku-20241022-v1:0"

def score_sentiment(text: str) -> float | None:
    try:
        response = bedrock_runtime.converse(
            modelId="anthropic.claude-3-5-haiku-20241022-v1:0",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": (
                                "You are a sentiment scoring function.\n"
                                "You MUST return ONLY one of these exact values:\n"
                                "-1.0, -0.5, 0.0, 0.5, 1.0\n"
                                "Do NOT explain.\n"
                                "Do NOT mention language.\n"
                                "Do NOT output anything except the number.\n\n"
                                f"Text:\n{text}"
                            )
                        }
                    ]
                }
            ],
            inferenceConfig={
                "temperature": 0,
                "maxTokens": 10
            }
        )

        output_text = response["output"]["message"]["content"][0]["text"].strip()

        try:
            value = float(output_text)
            if value in (-1.0, -0.5, 0.0, 0.5, 1.0):
                return value
        except Exception:
            pass

        print(f"⚠️ Sentiment parse failed. Raw output: {output_text!r}")
        return None

    except Exception as e:
        print(f"DEBUG: Claude sentiment failed: {e}")
        return None
