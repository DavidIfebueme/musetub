import { apiRequest } from './api';

export type ContactMessageRequest = {
  name: string;
  email: string;
  message: string;
};

export type CreatorAccessRequest = {
  name: string;
  email: string;
  channel_link?: string;
  message?: string;
};

export type ContactResponse = { status: string };

export async function sendContactMessage(payload: ContactMessageRequest): Promise<ContactResponse> {
  return apiRequest<ContactResponse>('/contact/message', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function requestCreatorAccess(payload: CreatorAccessRequest): Promise<ContactResponse> {
  return apiRequest<ContactResponse>('/contact/creator-access', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
