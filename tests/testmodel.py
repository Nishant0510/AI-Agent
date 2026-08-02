import ollama

client = ollama.Client(host="http://localhost:11434")

response = client.generate(
    model="qwen2.5:7b",  # replace with the exact name from `ollama list`
    prompt="Say hello"
)

print(response["response"])