import aiohttp
import asyncio
import uvicorn
import requests
from fastai import *
from fastai.vision import *
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

export_file_url = 'https://drive.google.com/uc?export=download&id=15V6P0q-nK9LJevvD8KIqOrMwi065v6Mh'
export_file_name = 'export-rand.pkl'

classes=["No_Finding", 
        "Enlarged_Cardiomediastinum", 
        "Cardiomegaly", 
        "Lung_Opacity", 
        "Lung_Lesion", 
        "Edema", 
        "Consolidation", 
        "Pneumonia", 
        "Atelectasis",
        "Pneumothorax",
        "Pleural_Effusion",
        "Pleural_Other",
        "Fracture",
        "Support_Devices",
        "Viral_Pneumonia",
        "Bacterial_Pneumonia",
        "Covid19",
        "Other"]
path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)

async def setup_learner():
    await download_file(export_file_url, path / export_file_name)
    try:
        learn = load_learner(path, export_file_name)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    img_data = await request.form()
    img_bytes = await (img_data['file'].read())
    img = open_image(BytesIO(img_bytes))
    thresh=0.53
    prediction = learn.predict(img, thresh=thresh)
    labels = str(prediction[0]).split(';')
    if labels==['']:
        answer="Other"
    else:
        probs = []
        for i in prediction[2]:
            if float(i)>thresh:
                probs.append(float(i))
        answer = dict(zip(labels, probs))
        sort_answer = sorted(answer.items(), key=lambda x: x[1], reverse=True)
        answer = []
        for label, prob in sort_answer:
            if label=="Other":
                answer.append(str(' '+label))
            else:
                answer.append(str(' '+label.replace('_', ' ')+': '+str(round(prob*100, 1))+'%'+" confident"))

    return JSONResponse({
		'result' : answer
		})


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
