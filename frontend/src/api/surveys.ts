import {request} from './client';import type {Survey} from '../types/domain';export const list=()=>request<Survey[]>('/surveys');
export const create=(data:unknown)=>request<Survey>('/surveys',data);
