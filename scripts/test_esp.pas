; Minimal test: Create one cell with one reference
unit TestSeydaNeen;

function Process(e: IInterface): Integer;
var
  espFile: IInterface;
  cellRecord: IInterface;
  refrRecord: IInterface;
begin
  AddMessage('Creating SeydaNeen.esp...');
  
  // Create new ESP
  espFile := AddNewFile('SeydaNeen.esp');
  if not Assigned(espFile) then
  begin
    AddMessage('Failed to create file');
    Exit;
  end;
  
  AddMessage('File created');
  
  // Add master
  AddMasterIfMissing(espFile, 'Starfield.esm');
  AddMessage('Added master');
  
  // Create a CELL record
  cellRecord := Add(espFile, 'CELL', True);
  if Assigned(cellRecord) then
  begin
    SetElementEditValues(cellRecord, 'EDID', 'TestCell');
    SetElementEditValues(cellRecord, 'CNAM', 1);
    AddMessage('Cell created');
  end;
  
  // Create a REFR record
  refrRecord := Add(espFile, 'REFR', True);
  if Assigned(refrRecord) then
  begin
    SetElementEditValues(refrRecord, 'EDID', 'TestRef');
    SetElementEditValues(refrRecord, 'DATA', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]);
    AddMessage('Reference created');
  end;
  
  AddMessage('Done!');
  Result := 1;
end;

end.
