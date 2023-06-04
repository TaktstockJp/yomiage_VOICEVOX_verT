@echo off
curl -s -H "Content-Type: application/json" -X POST -d @tmp/query.json localhost:%1/v1/synthesis > tmp/tmp_voice.wav