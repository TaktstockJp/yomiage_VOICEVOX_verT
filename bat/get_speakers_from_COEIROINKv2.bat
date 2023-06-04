@echo off
curl -s -X GET "localhost:%1/v1/speakers" > tmp/speakers.json