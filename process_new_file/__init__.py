import azure.functions as func
import os
from function_app import process_new_file

def main(event: func.EventGridEvent):
    return process_new_file(event)
