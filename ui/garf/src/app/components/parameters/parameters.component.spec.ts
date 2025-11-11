import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParametersComponent } from './parameters.component';

describe('ParametersComponent', () => {
  let component: ParametersComponent;
  let fixture: ComponentFixture<ParametersComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ParametersComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ParametersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
