def manage_input_output_paths(
    storage_type,
    input_path=None,
    output_path=None,
    input_bucket=None,
    output_bucket=None,
):

    reading_kwargs = {}
    writting_kwargs = {}

    if storage_type == "local":

        if not input_path:
            raise ValueError(
                "input_path is required when storage_type is 'local'"
            )

        if not output_path:
            raise ValueError(
                "output_path is required when storage_type is 'local'"
            )

        reading_kwargs["folder_path"] = input_path
        writting_kwargs["folder_path"] = output_path

    elif storage_type == "aws":

        input_bucket = input_bucket or os.getenv("S3_BUCKET_NAME")
        output_bucket = output_bucket or os.getenv("S3_BUCKET_NAME")

        if not input_bucket:
            raise ValueError("Missing input bucket")

        if not output_bucket:
            raise ValueError("Missing output bucket")

        reading_kwargs["bucket"] = input_bucket
        writting_kwargs["bucket"] = output_bucket

    return reading_kwargs, writting_kwargs