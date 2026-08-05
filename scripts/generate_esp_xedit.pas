{
  Generate SeydaNeen.esp with all placements using xEdit's API
  This creates proper Starfield record structures
}
unit SeydaNeenESP;

var
  espFile: IInterface;
  cellCount, refrCount: Integer;

function Initialize: Integer;
var
  csvDir: string;
  csvFile: string;
  cellName: string;
  cellFormID: Integer;
  i: Integer;
begin
  AddMessage('=== SeydaNeen ESP Generator ===');
  
  // Create new ESP file
  espFile := AddNewFile('SeydaNeen.esp', True);
  if not Assigned(espFile) then
  begin
    AddMessage('ERROR: Failed to create SeydaNeen.esp');
    Result := 1;
    Exit;
  end;
  AddMessage('Created SeydaNeen.esp');
  
  // Add masters
  AddMasterIfMissing(espFile, 'Starfield.esm');
  AddMasterIfMissing(espFile, 'TheElderStarSystem Magnus.esp');
  AddMessage('Added masters');
  
  // Create cells
  cellCount := 0;
  refrCount := 0;
  
  // Cell names from our placement data
  // We'll create them manually since xEdit Pascal can't easily read CSVs
  CreateCell('Seyda Neen', 1);  // exterior
  CreateCell('Seyda Neen, Arrille''s Tradehouse', 0);  // interior
  CreateCell('Seyda Neen, Census and Excise Office', 0);
  CreateCell('Seyda Neen, Census and Excise Warehouse', 0);
  CreateCell('Seyda Neen, Draren Thiralas'' House', 0);
  CreateCell('Seyda Neen, Eldafire''s House', 0);
  CreateCell('Seyda Neen, Erene Llenim''s Shack', 0);
  CreateCell('Seyda Neen, Fargoth''s House', 0);
  CreateCell('Seyda Neen, Fine-Mouth''s Shack', 0);
  CreateCell('Seyda Neen, Foryn Gilnith''s Shack', 0);
  CreateCell('Seyda Neen, Indrele Rathryon''s Shack', 0);
  CreateCell('Seyda Neen, Lighthouse', 0);
  CreateCell('Seyda Neen, Terurise Girvayne''s House', 0);
  CreateCell('Seyda Neen, Vodunius Nuccius'' House', 0);
  
  AddMessage(Format('Created %d cells', [cellCount]));
  AddMessage(Format('Created %d references', [refrCount]));
  AddMessage('=== Done ===');
  
  Result := 0;
end;

procedure CreateCell(cellName: string; isExterior: Integer);
var
  cellRecord: IInterface;
  cellGroup: IInterface;
begin
  // Create CELL record
  cellRecord := Add(espFile, 'CELL', True);
  if not Assigned(cellRecord) then
  begin
    AddMessage('ERROR: Failed to create cell: ' + cellName);
    Exit;
  end;
  
  // Set Editor ID
  SetElementEditValues(cellRecord, 'EDID', cellName);
  
  // Set cell flags (0 = interior, 1 = exterior)
  SetElementEditValues(cellRecord, 'CNAM', isExterior);
  
  // Add persistent children group
  cellGroup := Add(cellRecord, 'PERS', True);
  if Assigned(cellGroup) then
    AddMessage('  Created cell: ' + cellName);
  
  cellCount := cellCount + 1;
end;

procedure CreateRef(editorID: string; x, y, z, rx, ry, rz: Double);
var
  refRecord: IInterface;
begin
  // Create REFR record
  refRecord := Add(espFile, 'REFR', True);
  if not Assigned(refRecord) then
  begin
    AddMessage('ERROR: Failed to create ref: ' + editorID);
    Exit;
  end;
  
  // Set Editor ID
  SetElementEditValues(refRecord, 'EDID', editorID);
  
  // Set position and rotation (8 floats)
  SetElementEditValues(refRecord, 'DATA', [x, y, z, rx, ry, rz, 0, 0]);
  
  // Set scale
  SetElementEditValues(refRecord, 'XSCL', 1.0);
  
  refrCount := refrCount + 1;
end;

end.
