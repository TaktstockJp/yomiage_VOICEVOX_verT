@echo off
curl -s -X POST "localhost:%1/audio_query?text=%2&speaker=%3" > tmp/query.json