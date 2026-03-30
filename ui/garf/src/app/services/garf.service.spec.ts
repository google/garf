import { TestBed } from '@angular/core/testing';

import { GarfService } from './garf.service';

describe('GarfService', () => {
  let service: GarfService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(GarfService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
