
import { S3Client, GetObjectCommand, PutObjectCommand } from "@aws-sdk/client-s3";

export class S3Writer {
    constructor(region){
    this.client = new S3Client({
      region,
    });

  }

  /**
   * Upload an object to S3
   * @param {Object} params - Upload parameters
   * @param {string} params.bucket - S3 bucket name
   * @param {string} params.key - S3 object key
   * @param {string|Buffer} params.body - Object content
   * @param {string} params.contentType - MIME type of content
   * @returns {Promise} Upload result
   */
  async putObject({bucket, key, tsv_file_string}){
    const command = new PutObjectCommand({
        Bucket: bucket,
        Key: key,
        Body: tsv_file_string,
        ContentType: "text/tab-separated-values; charset=utf-8"
    });

    const result = await this.client.send(command);
    return result;
  }

  /**
   * Save a trajectory TSV to S3
   * @param {Object} params - Save parameters
   * @param {string} params.bucket - S3 bucket name
   * @param {string} params.parkId - Park ID (used as filename)
   * @param {string} params.tsvContent - TSV file content
   * @returns {Promise<Object>} Upload result with key
   */
  async saveTrajectory({bucket, parkId, tsvContent}) {
    const key = `${parkId}.tsv`;

    const result = await this.putObject({
      bucket,
      key,
      tsv_file_string: tsvContent
    });

    return {
      key,
      result
    };
  }
}