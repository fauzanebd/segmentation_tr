from pyscript import document, window
from pyscript import when
from io import BytesIO
import pandas as pd
from itertools import combinations
import scipy.stats as stats

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
    bucketing_cols = df.columns[df.columns.str.contains('^sum')].tolist()
    # drop nan custgroup
    df.drop(df.loc[df['custgroup'].isna()].index, axis=0, inplace=True)
    
    window.bucketing_cols = bucketing_cols  # Store in window object
    
    window.console.log("data loaded!")
    window.console.log(f"{df.shape[0]} rows and {df.shape[1]} columns")
    window.console.log(" ".join(df.columns))

    window.console.log("will show analysis")

    # Hide the upload prompt
    document.querySelector("#upload_prompt").style.display = "none"

    show_analysis(df, bucketing_cols)

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

    iframe_doc = qq_plot.contentDocument or qq_plot.contentWindow.document;
    iframe_doc.body.innerHTML = res['qq-graph']


# this only mockup to help create the UI
def show_analysis(df, bucketing_cols):
    # get analysis results
    # analysis_results = get_analysis_mock()
    analysis_results = find_best_groupings(df, bucketing_cols)
    
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




def aggregate_segment(data, groupings, bucketing_cols):
  final_data = pd.DataFrame()

  for group in groupings:
    window.console.log(f"group: {group}")
    sub_data = data.loc[data['custgroup'].isin(group)].copy()
    sub_data = sub_data.groupby(['period'])[bucketing_cols].sum().reset_index()
    sub_data['custgroup'] = " + ".join(group)
    final_data = pd.concat([final_data, sub_data], ignore_index=True)
  return final_data

class NormalityTestException(Exception):
  pass

class HomogenityTestException(Exception):
  pass

# this statistical_test function will be called by one groupings
# ex: [['A','B'], ['C']] is one groupings of ['A', 'B', 'C']
def statistical_test(data, groupings, bucketing_columns):
  print("bucketing columns at statistical test", bucketing_columns)
  # aggregate bucket values for grouped custgroup
  final_data = aggregate_segment(data, groupings, bucketing_columns)

  print(f"example grouping {groupings} result for period {final_data['period'].unique().tolist()[:3]}: {final_data.loc[final_data['period'].isin(final_data['period'].unique().tolist()[:3])]}")

  bucket_and_normtest_res = {}
  # normality test using shapiro-wilk
  for bucket in bucketing_columns:
    # Is metric within this bucket normally distributed?
    normality_res =  normality_test(final_data[bucket].dropna())
    if normality_res['shapiro_p'] >= 0.05:
      bucket_and_normtest_res[bucket] = True
    else:
      bucket_and_normtest_res[bucket] = False

  # only involve bucket passing normality test
  bucket_passing_normality_test = []
  for bucket, pass_norm_test in bucket_and_normtest_res.items():
    if pass_norm_test:
      bucket_passing_normality_test.append(bucket)


  print("bucket passing normality test", bucket_passing_normality_test)

  if len(bucket_passing_normality_test) < 1:
    raise NormalityTestException(f"Every bucket in data for grouping {groupings} is not normally distributed. Further test cannot be performed")

  # only use data with buckets that passing normality test
  final_data = final_data[['custgroup', 'period'] + bucket_passing_normality_test]

  # perform homogenity test on data that passing normality test
  homogenity_res = homogenity_test(final_data, bucket_passing_normality_test)
  if homogenity_res['levene_p'] >= 0.05:
    # if data passing homogenity test, then we perform anova
    anova_res = anova_test(final_data, bucket_passing_normality_test)
  else:
    raise HomogenityTestException(f"data for grouping {groupings} not passing homogenity test. ANOVA cannot be performed")

  return anova_res

def normality_test(column_values):
  shapiro_stat, shapiro_p = stats.shapiro(column_values)
  return {
      'shapiro_stat': shapiro_stat,
      'shapiro_p': shapiro_p
  }



def homogenity_test(data, bucketing_columns):
  print("bucketing columns at homogenity test", bucketing_columns)
  print("columns in data at homogenity test", data.columns)
  levene_stat, levene_p = stats.levene(*[data[col].dropna() for col in bucketing_columns])
  return {
      'levene_stat': levene_stat,
      'levene_p': levene_p
  }

def anova_test(data, bucketing_columns):
  anova_stat, anova_p = stats.f_oneway(*[data[col].dropna() for col in bucketing_columns])
  return {
      'anova_stat': anova_stat,
      'anova_p': anova_p
  }





def generate_all_groupings(values):
    result = []
    n = len(values)

    for i in range(1, n+1):
        if i == 1:
          result.append([[v] for v in values])
        else:
          for combo in combinations(values, i):
              group = list(combo)
              
              if n // i > 1:
                # if remaining possible to be combined
                remaining = [v for v in values if v not in group]
                remaining = generate_all_groupings(remaining)
                finalres = [[group] + rem for rem in remaining]
                result.extend(finalres)
              else:
                # if not, add the remaining
                remaining = [[v] for v in values if v not in group]
                result.append([group] + remaining)

    return result


def find_best_groupings(data, bucketing_columns):

  custgroup_values = data['custgroup'].unique().tolist()
  all_possible_groupings = generate_all_groupings(custgroup_values)
  
  grouping_results = []
  for groupings in all_possible_groupings:
    
    print("testing grouping: ", groupings)
    anova_res = {
        'anova_stat': 1000,
        'anova_p': 1000,
    }
    try:
      anova_res = statistical_test(data, groupings, bucketing_columns) #df will be copied inside statistical_test so it wont be override each iteration
    except NormalityTestException:  
      pass
    except HomogenityTestException:
      # set p value high
      pass
    print("result: ", anova_res)

    grouping_res = {
        'grouping_id': f"{groupings}",
        'anova_statistic': anova_res['anova_stat'],
        'anova_p': anova_res['anova_p']
    }
    grouping_results.append(grouping_res)

    # will return this:
    #  {
    #   'grouping_result': [
    #       {
    #           'grouping_id': 'A+B+C',
    #           'anova_statistic': 2334,
    #           'anova_p': 0.034
    #       },
    #       {
    #           'grouping_id': 'A+B+C',
    #           'anova_statistic': 2334,
    #           'anova_p': 0.034
    #       },
    #       {
    #           'grouping_id': 'A+B+C',
    #           'anova_statistic': 2334,
    #           'anova_p': 0.034
    #       },
    #     ]
    # }
  
  # sort based on anova value
  temp_df = pd.DataFrame(grouping_results)
  print(temp_df['anova_p'].min())
  temp_df.sort_values(by='anova_p', ascending=True, inplace=True)
  grouping_results = temp_df.to_dict('records')


  return {'grouping_result': grouping_results[:3]}

def get_normality_analysis_detail_mock(grouping_id, bucket_id):
  return {
    'qq-graph': f"""
       <!DOCTYPE html>
<html>
<head>
</head>
<body>
    <h2>Q-Q Plot for Segment {grouping_id} and Bucket {bucket_id}</h2>
</body>
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