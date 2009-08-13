/* 
 *  This file is part of the RECAP Firefox Extension.
 *
 *  Copyright 2009 Harlan Yu, Timothy B. Lee, Stephen Schultze.
 *  Website: http://www.recapthelaw.org
 *  E-mail: info@recapthelaw.org
 *
 *  The RECAP Firefox Extension is free software: you can redistribute it 
 *  and/or modify it under the terms of the GNU General Public License as
 *  published by the Free Software Foundation, either version 3 of the 
 *  License, or (at your option) any later version.
 *
 *  The RECAP Firefox Extension is distributed in the hope that it will be
 *  useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with the RECAP Firefox Extension.  If not, see 
 *  <http://www.gnu.org/licenses/>.
 *
 */

var pdfHeadersCheckbox;
pdfHeadersCheckbox = document.getElementsByName("pdf_header");
if (pdfHeadersCheckbox.length > 0) {	
	pdfHeadersCheckbox[0].checked=true;
}
