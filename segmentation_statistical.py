from pyscript import document, window
from pyscript import when
from io import BytesIO
import pandas as pd

import warnings
warnings.filterwarnings("ignore", "\nPyarrow", DeprecationWarning)


@when("change", "#file_upload")
async def handle_file_upload(event):
    window.console.log("file uploaded!")
    file = document.querySelector("#file_upload").files.item(0)

    file_type = file.type

    window.console.log(file_type)

    array_buf = await file.arrayBuffer()
    file_bytes = array_buf.to_bytes()
    file_byteIO = BytesIO(file_bytes)

    if file_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        df = pd.read_excel(file_byteIO, engine="openpyxl")
        
    elif file_type == "text/csv":
        df = pd.read_csv(file_byteIO)
    
    else:
        raise ValueError("Unsupported file type")

    window.console.log("data loaded!")
    window.console.log(f"{df.shape[0]} rows and {df.shape[1]} columns")
    window.console.log(" ".join(df.columns))



    # generate_segmentations()

    
    

    
    # if file:
    #     document.querySelector("#upload_prompt").style.display = "none"
    #     document.querySelector("#possible_segmentations").style.display = "block"
    #     document.querySelector("#result_section").style.display = "block"
        
        # Placeholder: Process the file and generate segmentations
        # generate_segmentations()
        
        # Placeholder: Perform analysis and display results
        # perform_analysis()


def perform_analysis():
    results_list = document.querySelector("#results_list")
    results_list.innerHTML = """
        <div class="card mb-3">
            <div class="card-body">
                <h5 class="card-title">1. Possible Segment 3</h5>
                <p class="card-text">ANOVA results:<br>Statistics: 3.32<br>P-value: 0.034</p>
                <button class="btn btn-primary" onclick="show_detailed_analysis('Segment 3')">Detailed Analysis</button>
                <button class="btn btn-secondary">Download segmented excel file</button>
            </div>
        </div>
        <div class="card mb-3">
            <div class="card-body">
                <h5 class="card-title">2. Possible Segment 1</h5>
                <p class="card-text">ANOVA results:<br>Statistics: 3.12<br>P-value: 0.043</p>
                <button class="btn btn-primary" onclick="show_detailed_analysis('Segment 1')">Detailed Analysis</button>
                <button class="btn btn-secondary">Download segmented excel file</button>
            </div>
        </div>
    """

# def show_detailed_analysis(segment):
#     modal = js.bootstrap.Modal.getInstance(document.querySelector('#detailed_analysis_modal'))
#     if not modal:
#         modal = js.bootstrap.Modal(document.querySelector('#detailed_analysis_modal'))
#     modal.show()

# Event listener for file upload
# document.querySelector("#file_upload").addEventListener("change", handle_file_upload)

# # Make show_detailed_analysis available to JavaScript
# js.window.show_detailed_analysis = show_detailed_analysis