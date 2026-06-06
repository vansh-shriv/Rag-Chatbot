from extractors.instagram import extract_instagram

result = extract_instagram("https://www.instagram.com/reel/DZMvu7rTC-I")

print("Creator:",result["metadata"]["creator"])
print("Followers:", result["metadata"]["followers"])
print("Views:", result["metadata"]["views"])
print("Likes:", result["metadata"]["likes"])
print("Comments:", result["metadata"]["comments"])
print("Engagement Rate:", result["metadata"]["engagement_rate"], "%")
print("Caption/Transcript:", result["transcript_text"][:300])

