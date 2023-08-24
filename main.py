from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from os import listdir, remove
from os.path import isfile, join
from shutil import copy
import datetime

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


"""
This is a FastAPI script used to power a notebook with automated dates.
The primary purpose is to have an accessible and searchable notebook,
locally hosted for my own sanity.


py -m uvicorn main:app --reload
"""

# Boot up the app
app = FastAPI() # app to start the FastAPI
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=join("static", "templates"))


"""
Data classes necessary for the app. Required to format inputs
"""
class Note(BaseModel):
    str_data: str

class Query(BaseModel):
    str_data: str


"""
API methods that power the pages
"""
@app.post("/note")
def post_note(note: Note):
    """
    An API that takes an ASCII string as POST data and creates a local
    text file. The text file is named after the date written.
    """
    cur_time = datetime.datetime.now().strftime("20%y_%m_%d__%H___%M___%S")
    filename = join("note", f"{cur_time}.txt")
    
    with open(filename, "w") as fh:
        fh.write(note.str_data)
    
    result = f"Note {filename} was successfully written."
    
    return {"result": result}
    

@app.post("/search")
def search_notes(search: Query):
    """
    An API that takes an ASCII string as POST data and searches a fixed
    local folder for files. Returns a list of filenames.
    """
    
    # get a list of all the notefiles in the notefolder
    notes = [join("note", filename) for filename in listdir("note") \
             if isfile(join("note", filename))]
    
    ret_notes = []
    
    # lowercase the query
    query = search.str_data.lower()
    
    for note in notes:
        with open(note, "r") as fh:
            data = fh.read()
            if query.lower() in data:
                ret_notes.append(note)
                
    # get a list of all the notefiles in the searchfolder
    del_notes = [join("search", filename) for filename in listdir("search") \
             if isfile(join("search", filename))]
    
    # remove all items in the search folder    
    for note in del_notes:
        remove(note)

    # copy all new search results into folder
    for note in ret_notes:
        copy(note, note.replace("note", "search"))

    # cp all se
    return {"result": ret_notes}
    
    
@app.get("/browse/{item_id}")
def browser_results(item_id: int, request: Request):
    """
    An API to browse items located in the search folder
    """
    
    notes = listdir("search")
    
    if item_id >= len(notes) or item_id < 0:
        raise HTTPException(status_code=404, detail="Item not found")
        
    notes.sort()
    
    with open(join("search", notes[item_id]), "r") as fh:
        data = fh.read()
        
    date = notes[item_id].replace("___", ":") \
                         .replace("__", " ")  \
                         .replace("_", "-")   \
                         .replace(".txt", "")

    context = {"request": request, "date": date, "data": data, "item_id": item_id}
    return templates.TemplateResponse("browse.html", context)


@app.get("/", response_class=HTMLResponse)
def front_page(request: Request):
    """
    Primary front page for the app.
    """
    return templates.TemplateResponse("homepage.html", {"request": request})
    