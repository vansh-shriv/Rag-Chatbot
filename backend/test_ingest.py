from ingest import ingest_videos

result = ingest_videos(
    youtube_url="https://youtu.be/9t-kEXX6Ogw?si=LBFBJaLJ0OnMmOjh",
    instagram_url="https://www.instagram.com/reel/DZMvu7rTC-I"
)

print(f"Result")
print(f"Video A:",result["video_a"]["metadata"]["title"])
print(f"Video A engagement:",result["video_a"]["metadata"]["engagement_rate"],"%")
print(f"Video B:",result["video_b"]["metadata"]["title"])
print(f"Video B engagement:",result["video_b"]["metadata"]["engagement_rate"],"%")