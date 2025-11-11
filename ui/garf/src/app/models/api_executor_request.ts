export interface QueryParameters {
  macro: Map<string, string>;
  template: Map<string, string>;
}

export interface ApiExecutionContext {
  queryParameters: QueryParameters;
  fetcherParameters: Map<string, string>;
  writer: string;
  writerOptions: Map<string, string>;
}

export interface ApiExecutionRequest {
  source: string;
  title: string;
  query: string;
  context: ApiExecutionContext;
}
