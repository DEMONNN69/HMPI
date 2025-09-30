import React from 'react';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { GroundWaterSample } from '../lib/api';

interface GroundWaterSamplesTableProps {
  samples: GroundWaterSample[];
  isLoading: boolean;
}

export function GroundWaterSamplesTable({ samples, isLoading }: GroundWaterSamplesTableProps) {
  if (isLoading) {
    return <div className="flex justify-center p-8">Loading ground water samples...</div>;
  }

  if (samples.length === 0) {
    return <div className="flex justify-center p-8">No ground water samples found.</div>;
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableCaption>Ground Water Samples Database</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>S.No</TableHead>
            <TableHead>State</TableHead>
            <TableHead>District</TableHead>
            <TableHead>Location</TableHead>
            <TableHead>Longitude</TableHead>
            <TableHead>Latitude</TableHead>
            <TableHead>Year</TableHead>
            <TableHead>pH</TableHead>
            <TableHead>EC (µS/cm)</TableHead>
            <TableHead>Heavy Metals</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {samples.map((sample) => (
            <TableRow key={sample.id}>
              <TableCell>{sample.s_no}</TableCell>
              <TableCell>{sample.state}</TableCell>
              <TableCell>{sample.district}</TableCell>
              <TableCell>{sample.location}</TableCell>
              <TableCell>{sample.longitude}</TableCell>
              <TableCell>{sample.latitude}</TableCell>
              <TableCell>{sample.year}</TableCell>
              <TableCell>{sample.ph || 'N/A'}</TableCell>
              <TableCell>{sample.ec_us_cm || 'N/A'}</TableCell>
              <TableCell>
                <div className="flex flex-col space-y-1 text-xs">
                  <span>Fe: {sample.fe_ppm !== null ? `${sample.fe_ppm} ppm` : 'N/A'}</span>
                  <span>As: {sample.as_ppb !== null ? `${sample.as_ppb} ppb` : 'N/A'}</span>
                  <span>U: {sample.u_ppb !== null ? `${sample.u_ppb} ppb` : 'N/A'}</span>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}