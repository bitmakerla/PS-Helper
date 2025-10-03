import uuid
import boto3


def upload_html_to_s3(
    html_str: str,
    bucket: str,
    key: str = None,
    publico: bool = False,
    expira_seg: int = 3 * 24 * 3600
):
    """
    Uploads HTML to S3 from memory.

    Args:
        html_str: HTML content as string
        bucket: S3 bucket name
        key: S3 path (optional, generates UUID if not provided)
        publico: If True, makes the file public
        expira_seg: Expiration seconds for private URL (default 30 days)

    Returns:
        str: File URL (public or signed)
    """

    s3 = boto3.client("s3")
    key = key or f"reports/{uuid.uuid4()}.html"

    put_args = dict(
        Bucket=bucket,
        Key=key,
        Body=html_str.encode("utf-8"),
        ContentType="text/html; charset=utf-8"
    )

    if publico:
        put_args["ACL"] = "public-read"

    s3.put_object(**put_args)

    if publico:
        url = f"https://{bucket}.s3.amazonaws.com/{key}"
    else:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expira_seg
        )

    return url
