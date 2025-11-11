import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { QueryAreaComponent } from './components/query-area/query-area.component';
import { ParametersComponent } from './components/parameters/parameters.component';
import { PreviewComponent } from './components/preview/preview.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    QueryAreaComponent,
    ParametersComponent,
    PreviewComponent,
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  title = 'garf';
}
