import { DynamoDBClient,  ScanCommand, PutItemCommand } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, GetCommand } from "@aws-sdk/lib-dynamodb";

export class DynamoDbReader {
  constructor(region, tableName) {
    // Use default AWS credential chain (instance role on EC2, env vars/~/.aws/credentials locally)
    this.dynamoClient = new DynamoDBClient({
      region,
    });
    this.tableName = tableName;
  }

  async scanItems({limit = 100}) {
    const params = { TableName: this.tableName, Limit: limit };
    const command = new ScanCommand(params);
    return await this.dynamoClient.send(command)
  }

  async getItem(key) {
    const command = new GetCommand({
      ConsistentRead: true,
      TableName: this.tableName,
      Key: key,
    });
    const documentClient = DynamoDBDocumentClient.from(this.dynamoClient)

    const response = await documentClient.send(command);
    console.log(response);
    return response;

  }

  /**
   * Get leaderboard entries
   * @param {number} limit - Maximum number of entries to return (default: 100)
   * @returns {Promise<Object>} Leaderboard data with entries and count
   */
  async getLeaderboard({limit = 100} = {}) {
    try {
      const results = await this.scanItems({limit});

      // console.log('DynamoDB scan results:', JSON.stringify(results, null, 2));

      // Handle case where Items might be undefined or not an array
      if (!results || !results.Items || !Array.isArray(results.Items)) {
        console.error('Invalid DynamoDB scan response:', results);
        return {
          leaderboard: [],
          count: 0
        };
      }

      // Convert DynamoDB format to plain objects
      const leaderboard = results.Items.map(item => {
        const newEntry = {};
        const keys = Object.keys(item);

        for (let i = 0; i < keys.length; i++) {
          let key = keys[i];
          const value = item[key][Object.keys(item[key])[0]];
          newEntry[key] = value;
        }

        return newEntry;
      });

      return {
        leaderboard,
        count: results.Count || 0
      };
    } catch (error) {
      console.error('Error in getLeaderboard:', error);
      return {
        leaderboard: [],
        count: 0
      };
    }
  }
}

export class DynamoDBWriter {

  constructor(region, tableName) {
    // Use default AWS credential chain (instance role on EC2, env vars/~/.aws/credentials locally)
    this.dynamoClient = new DynamoDBClient({
      region,
    });

    this.tableName = tableName;
  }

  async putItem(item) {
    const params = {
      TableName: this.tableName,
      Item: item,
    };

    const command = new PutItemCommand(
      params
    )
    const result = await this.dynamoClient.send(command)
    return result
  }

  /**
   * Create a leaderboard entry
   * @param {Object} params - Entry parameters
   * @param {string} params.parkId - Park ID
   * @param {boolean} params.is_human - Whether entry is from human or AI
   * @param {string} params.name - Name (username for humans, model name for AI)
   * @param {string} params.resource_setting - Resource setting (few-shot, few-shot+docs, unlimited)
   * @param {string} params.difficulty - Difficulty level (easy, medium, hard)
   * @param {string} params.layout - Park layout name
   * @param {number} params.score - Final score
   * @param {boolean} params.validated - Whether the entry has been validated (default: false)
   * @param {number} params.cost - Cost (optional)
   * @param {number} params.timeTaken - Time taken in milliseconds (optional)
   * @param {string} params.repoLink - Repository link (optional)
   * @param {string} params.paperLink - Paper link (optional)
   * @returns {Promise} DynamoDB put result
   */
  async createLeaderboardEntry({
    parkId,
    is_human,
    name,
    resource_setting,
    difficulty,
    layout,
    score,
    validated = false,
    cost = null,
    timeTaken = null,
    repoLink = null,
    paperLink = null
  }) {

    const item = {
      parkId: { 'S': `${parkId}` },
      is_human: { 'BOOL': is_human },
      name: { 'S': name },
      resource_setting: { 'S': resource_setting },
      difficulty: { 'S': difficulty },
      layout: { 'S': layout },
      score: { 'N': `${score}` },
      validated: { 'BOOL': validated }
    };

    // Add optional fields only if they are provided
    if (cost !== null) {
      item.cost = { 'N': `${cost}` };
    }
    if (timeTaken !== null) {
      item.timeTaken = { 'N': `${timeTaken}` };
    }
    if (repoLink !== null && repoLink !== '') {
      item.repoLink = { 'S': repoLink };
    }
    if (paperLink !== null && paperLink !== '') {
      item.paperLink = { 'S': paperLink };
    }

    console.log("DynamoDB item to be saved:");
    console.log(JSON.stringify(item, null, 2));
    console.log("Table name:", this.tableName);

    try {
      const result = await this.putItem(item);
      return result;
    } catch (error) {
      throw error;
    }
  }
}
