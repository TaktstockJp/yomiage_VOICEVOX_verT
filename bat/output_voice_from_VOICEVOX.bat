@echo off
curl -s -H "Content-Type: application/json" -X POST -d @tmp/query.json localhost:%1/synthesis?speaker=%2 > tmp/tmp_voice.wav