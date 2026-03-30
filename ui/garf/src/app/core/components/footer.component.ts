import { Component, inject } from '@angular/core';
import { GarfService } from './../../services/garf.service';

@Component({
  selector: 'app-footer',
  imports: [],
  template: '<p>Garf Version: {{version}}</p>',
})
export class FooterComponent {
  private garfService = inject(GarfService);
  version: string = '';

  ngOnInit() {
    this.garfService.getVersion().subscribe((version) => (this.version = version));
  }
}
