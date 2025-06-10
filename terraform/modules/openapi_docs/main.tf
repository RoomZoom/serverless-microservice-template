# terraform/modules/openapi_docs/main.tf
resource "aws_s3_bucket" "openapi_docs" {
  bucket = var.bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "block" {
  bucket = aws_s3_bucket.openapi_docs.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "public_read" {
  bucket = aws_s3_bucket.openapi_docs.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "PublicReadGetObject",
        Effect    = "Allow",
        Principal = "*",
        Action    = ["s3:GetObject"],
        Resource  = ["${aws_s3_bucket.openapi_docs.arn}/*"]
      }
    ]
  })
}

resource "aws_cloudfront_distribution" "docs_cdn" {
  origin {
    domain_name = aws_s3_bucket.openapi_docs.bucket_regional_domain_name
    origin_id   = "S3-origin"
  }

  enabled             = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-origin"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

output "openapi_docs_url" {
  value = "https://${aws_cloudfront_distribution.docs_cdn.domain_name}"
}