import { Component, inject } from '@angular/core';
import { GarfService } from './../../services/garf.service';

@Component({
  selector: 'app-footer',
  imports: [],
  templateUrl: './footer.component.html',
  styleUrl: './footer.component.css'
})
export class FooterComponent {
  private garfService = inject(GarfService);
  version: string = '';

  ngOnInit() {
    this.garfService.getVersion().subscribe((version) => (this.version = version));
  }
}
