import { Component, inject } from '@angular/core';
import { GarfService } from './../../services/garf.service';

@Component({
  selector: 'app-footer',
  imports: [],
  template: `
  <p>Garf Version: {{version}}</p>
  <p> Available Fetchers: {{fetchers}}</p>
  `,
})
export class FooterComponent {
  private garfService = inject(GarfService);
  version: string = '';
  fetchers: string = '';

  ngOnInit() {
    this.garfService.getVersion().subscribe((version) => (this.version = version));
    this.garfService.getFetchers().subscribe((fetchers) => (this.fetchers = fetchers));
  }
}
