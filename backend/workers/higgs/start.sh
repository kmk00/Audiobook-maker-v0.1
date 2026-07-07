#!/bin/zsh
set -e

cd /workspace

if [ ! -d "sglang-omni/.git" ]; then
  echo ">>> Klonowanie repo..."
  rm -rf sglang-omni
  git clone https://github.com/sgl-project/sglang-omni.git
fi

cd sglang-omni

rm -rf docs/_static/audio
ln -s /workspace/app_backend docs/_static/audio

if [ ! -f ".venv/bin/activate" ]; then
  echo ">>> Tworzenie venv i instalacja..."
  uv venv .venv -p 3.12
  source .venv/bin/activate
  uv pip install -v -e .
else
  source .venv/bin/activate
fi

echo ">>> Sprawdzanie/pobieranie modelu..."
hf download bosonai/higgs-audio-v3-tts-4b

echo ">>> Startuje serwer..."
exec sgl-omni serve \
  --model-path bosonai/higgs-audio-v3-tts-4b \
  --allowed-local-media-path docs/_static/audio \
  --port 8000