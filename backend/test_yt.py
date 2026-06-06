from extractors.youtube import extract_youtube

result = extract_youtube("https://youtu.be/9t-kEXX6Ogw?si=LBFBJaLJ0OnMmOjh")

print("Title:",result["metadata"]["title"])
print("Creator:", result["metadata"]["creator"])
print("Likes:",result["metadata"]["likes"])
print("Comments:",result["metadata"]["comments"])
print("Views:",result["metadata"]["views"])
print("Engagement:",result["metadata"]["engagement_rate"],"%")
print("Transcript preview:",result["transcript_text"][:200])