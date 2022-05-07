from source_name import *
import time
import json

if __name__ == '__main__':
    start_time = time.time()

    a = Handler()
    # final_data = a.Execute('aHR0cHM6Ly93d3cudmFsdWUudG9kYXkvY29tcGFueS9hbC1yYWpoaS1iYW5raW5nLWFuZC1pbnZlc3RtZW50LWNvcnBvcmF0aW9u=',
    #                        'Financial_Information', '', '')
    final_data = a.Execute('Bank','','','')
    # final_data = a.Execute('MDA0MDAwPz1MT1RURSBGaW5lIENoZW1pY2Fs', 'graph:shareholders', '', '')
    # final_data = a.Execute('aHR0cHM6Ly93d3cudmFsdWUudG9kYXkvY29tcGFueS9iYW5rLWFtZXJpY2EtY29ycG9yYXRpb24=',
    #                         'officership','','')
    print(json.dumps(final_data, indent=4))

    elapsed_time = time.time() - start_time
    print('\nTask completed - Elapsed time: ' + str(round(elapsed_time, 2)) + ' seconds')
