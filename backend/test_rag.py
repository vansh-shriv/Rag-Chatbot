from rag_agent import chat

questions = [
    "What is the engagement rate of each video?",
    "Why did one video get more engagement than the other?",
    "Compare the hooks in the first 5 seconds of both videos",
    "Who is the creator of Video B?",
    "Suggest improvements for Video B based on what worked in Video A",
]

thread = "test-session-001"

for q in questions:
    print(f"\n{'='*60}")
    print(f"Q:{q}")
    result = chat(q,thread_id=thread)
    print(f"A: {result['answer']}")
    print(f"Sources: {result['sources']}")

    