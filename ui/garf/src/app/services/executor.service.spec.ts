import { TestBed } from '@angular/core/testing';

import { ExecutorService } from './executor.service';

describe('ExecutorService', () => {
  let service: ExecutorService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ExecutorService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
