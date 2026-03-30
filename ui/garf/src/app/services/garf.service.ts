import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class GarfService {
  private httpClient = inject(HttpClient);

  getVersion() {
    return this.httpClient.get<string>('api/version');
  }
  getFetchers() {
    return this.httpClient.get<string>('api/fetchers');
  }
}
