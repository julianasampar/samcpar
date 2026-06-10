import os 

def manage_input_output_paths(
    storage_type,
    io_type:str,
    input_path=None,
    output_path=None,
    input_bucket=None,
    output_bucket=None,
):

    reading_kwargs = {}
    writting_kwargs = {}

    if storage_type == "local":
        
        if io_type == "profiler-inspector":

            reading_kwargs["folder_path"] = input_path or os.getenv("PROFILER_PATH")
            writting_kwargs["folder_path"] = output_path or os.getenv("INPESCTOR_PATH")

            if not reading_kwargs["folder_path"]:
                raise ValueError(
                    "Please, provide input_path or add PROFILER_PATH in your environment variables."
                )

            if not writting_kwargs["folder_path"]:
                raise ValueError(
                     "Please, provide output_path or add INPESCTOR_PATH in your environment variables."
                )

        if io_type == "inspector-analyzer":

            reading_kwargs["folder_path"] = input_path or os.getenv("INPESCTOR_PATH")
            writting_kwargs["folder_path"] = output_path or os.getenv("ANALYZER_PATH")

            if not reading_kwargs["folder_path"]:
                raise ValueError(
                    "Please, provide input_path or add INPESCTOR_PATH in your environment variables."
                )

            if not writting_kwargs["folder_path"]:
                raise ValueError(
                     "Please, provide output_path or add ANALYZER_PATH in your environment variables."
                )

    elif storage_type == "aws":

        if io_type == "profiler-inspector":

            input_bucket = input_bucket or os.getenv("S3_PROFILER_BUCKET")
            output_bucket = output_bucket or os.getenv("S3_INSPECTOR_BUCKET")

            if not input_bucket:
                raise ValueError(
                     "Please, provide input_bucket or add S3_PROFILER_BUCKET in your environment variables."
                )

            if not output_bucket:
                raise ValueError(
                     "Please, provide output_bucket or add S3_INSPECTOR_BUCKET in your environment variables."
                )

        
        if io_type == "inspector-analyzer":
            input_bucket = input_bucket or os.getenv("S3_INSPECTOR_BUCKET")
            output_bucket = output_bucket or os.getenv("S3_ANALYZER_BUCKET")

            if not input_bucket:
                raise ValueError(
                     "Please, provide input_bucket or add S3_INSPECTOR_BUCKET in your environment variables."
                )

            if not output_bucket:
                raise ValueError(
                     "Please, provide output_bucket or add S3_ANALYZER_BUCKET in your environment variables."
                )


        reading_kwargs["bucket"] = input_bucket
        writting_kwargs["bucket"] = output_bucket

    return reading_kwargs, writting_kwargs