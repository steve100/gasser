
echo "Restart Clean" 
echo "start and stop the server"
lms server stop
lms server start

echo "unload all models"
lms unload --all

rem #it will do a scarch because this is not preciese
rem lms load "qwen2.5-vl-7b-instruct@q8_0 --gpu=max 

echo "load the model we want to test now "
lms load "lmstudio-community/Qwen2.5-VL-7B-Instruct-GGUF/Qwen2.5-VL-7B-Instruct-Q8_0.gguf" --gpu=max

echo "list currently loaded models"
lms ps

echo "see if lmstudio and the model will answer a promt"
curl http://localhost:1234/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\": \"qwen/qwen2.5-7b-instruct-q8_0\", \"messages\": [{\"role\": \"user\", \"content\": \"In one sentence, who are you?\"}], \"temperature\": 0.7, \"max_tokens\": 50}"

lms ps
