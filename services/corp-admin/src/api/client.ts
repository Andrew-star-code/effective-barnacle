import createClient from 'openapi-fetch'

import type { paths } from './schema'

// Типы — из OpenAPI corp-ext: `make gen-api` (schema.d.ts руками не правится).
export const api = createClient<paths>({ baseUrl: '/' })
