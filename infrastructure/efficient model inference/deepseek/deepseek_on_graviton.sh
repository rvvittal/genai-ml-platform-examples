# Clone llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# build with cmake
mkdir build
cd build
cmake .. -DCMAKE_CXX_FLAGS="-mcpu=native" -DCMAKE_C_FLAGS="-mcpu=native"
cmake --build . -v --config Release -j `nproc`

# Download model
cd bin
wget https://huggingface.co/bartowski/DeepSeek-R1-Distill-Llama-70B-GGUF/resolve/main/DeepSeek-R1-Distill-Llama-70B-Q4_0.gguf

# Running model inference with llama.cpp cli
./llama-cli -m DeepSeek-R1-Distill-Llama-70B-Q4_0.gguf -p "Building a visually appealing website can be done in ten simple steps:/" -n 512 -t 64 