import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QueryAreaComponent } from './query-area.component';

describe('QueryAreaComponent', () => {
  let component: QueryAreaComponent;
  let fixture: ComponentFixture<QueryAreaComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QueryAreaComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(QueryAreaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
