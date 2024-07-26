from pyscript import document, window
from pyscript import when
from io import BytesIO
import pandas as pd

import warnings
warnings.filterwarnings("ignore", "\nPyarrow", DeprecationWarning)

# Store bucketing_cols globally
window.bucketing_cols = []
window.segment_id = 0

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

    df.drop(df.columns[df.columns.str.contains('^Unnamed')], axis=1, inplace=True)
    df.columns = df.columns.str.lower()
    bucketing_cols = df.columns[df.columns.str.contains('^sum')]
    window.bucketing_cols = bucketing_cols.tolist()  # Store in window object
    
    window.console.log("data loaded!")
    window.console.log(f"{df.shape[0]} rows and {df.shape[1]} columns")
    window.console.log(" ".join(df.columns))

    window.console.log("will show analysis")

    # Hide the upload prompt
    document.querySelector("#upload_prompt").style.display = "none"

    show_analysis()

# Event handler when user clicks on detailed analysis
def show_detailed_analysis(event):
    # Get the value of the attr data-segment-id from the button
    window.segment_id = event.target.getAttribute("data-grouping-id")

    # Access bucketing_cols from window
    bucketing_cols = window.bucketing_cols

    # select options bucketing_cols
    bucket_select = document.querySelector("#bucket_select")
    options_bucket = "<option value=''>Select a bucket</option>"

    for i, col in enumerate(bucketing_cols):
        options_bucket += f"<option value={col}>{col}</option>"

    bucket_select.innerHTML = options_bucket

    window.console.log(f"Bucketing Columns: {bucketing_cols}")
    window.console.log("show detailed analysis")

@when("change", "#bucket_select")
async def handle_bucket_change(event):
    selected_bucket = document.querySelector("#bucket_select").value
    window.console.log(f"Selected bucket: {selected_bucket} for segment {window.segment_id}")
    
    res = get_normality_analysis_detail_mock(window.segment_id, selected_bucket)

    qq_plot = document.querySelector("#qq_plot")
    qq_plot.innerHTML = res['qq-graph']


# this only mockup to help create the UI
def show_analysis():
    # get analysis results
    analysis_results = get_analysis_mock()
    
    # Assuming you have a way to interact with the DOM in Python, such as Brython or Pyodide
    result_list = document.querySelector("#results_list")
    result_list.innerHTML = ""
    
    for i, result in enumerate(analysis_results['grouping_result']):
        # Create a new div for each result
        result_card = document.createElement('div')
        result_card.className = "segment-card"
        
        # Create the HTML content for each result card
        result_content = f"""
            <div class="card my-3" style="width: 40rem">
                <div class="card-body">
                                <h4>{i + 1}. Possible Segment {result['grouping_id']}</h4>
                                <p><strong>ANOVA results:</strong></p>
                                <p>Statistics: {result['anova_statistic']}<br>P-Value: {result['anova_p']}</p>
                                <div class="d-flex justify-content-between">
                                    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#detailed_analysis_modal" data-grouping-id={result['grouping_id']} py-click="show_detailed_analysis">Detailed Analysis</button>
                                    <button class="btn btn-secondary">Download segmented excel file</button>
                                </div>
                            </div>
            </div>
        """
        
        # Set the innerHTML of the result card
        result_card.innerHTML = result_content
        
        # Append the result card to the result list
        result_list.appendChild(result_card)
    
    # remove display none on result_section
    document.querySelector("#result_section").style.display = "block"

# Mock function to simulate getting analysis results
def get_analysis_mock():
    return {
        'grouping_result': [
            {
                'grouping_id': 'A+B+C',
                'anova_statistic': 2334,
                'anova_p': 0.034
            },
            {
                'grouping_id': 'D+E+F',
                'anova_statistic': 3120,
                'anova_p': 0.043
            },
            {
                'grouping_id': 'G+H+I',
                'anova_statistic': 2987,
                'anova_p': 0.029
            },
        ]
    }

def get_normality_analysis_detail_mock(grouping_id, bucket_id):
  return {
    'qq-graph': f"""
        <html>
            <h1>QQ Plot for {grouping_id} - {bucket_id}</h1>
        </html>
    """,
    'shapiro_statistic': 243,
    'shapiro_pvalue': 0.43343,
  }



# def perform_analysis():
#     results_list = document.querySelector("#results_list")
#     results_list.innerHTML = """
#         <div class="card mb-3">
#             <div class="card-body">
#                 <h5 class="card-title">1. Possible Segment 3</h5>
#                 <p class="card-text">ANOVA results:<br>Statistics: 3.32<br>P-value: 0.034</p>
#                 <button class="btn btn-primary" onclick="show_detailed_analysis('Segment 3')">Detailed Analysis</button>
#                 <button class="btn btn-secondary">Download segmented excel file</button>
#             </div>
#         </div>
#         <div class="card mb-3">
#             <div class="card-body">
#                 <h5 class="card-title">2. Possible Segment 1</h5>
#                 <p class="card-text">ANOVA results:<br>Statistics: 3.12<br>P-value: 0.043</p>
#                 <button class="btn btn-primary" onclick="show_detailed_analysis('Segment 1')">Detailed Analysis</button>
#                 <button class="btn btn-secondary">Download segmented excel file</button>
#             </div>
#         </div>
#     """

# def show_detailed_analysis(segment):
#     modal = js.bootstrap.Modal.getInstance(document.querySelector('#detailed_analysis_modal'))
#     if not modal:
#         modal = js.bootstrap.Modal(document.querySelector('#detailed_analysis_modal'))
#     modal.show()

# Event listener for file upload
# document.querySelector("#file_upload").addEventListener("change", handle_file_upload)

# # Make show_detailed_analysis available to JavaScript
# js.window.show_detailed_analysis = show_detailed_analysis