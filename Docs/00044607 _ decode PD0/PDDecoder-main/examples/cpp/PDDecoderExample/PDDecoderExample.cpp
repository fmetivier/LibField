/** @file PD0DecoderExample.cpp
 *  @brief Example in C++ to show how to use library
 * 
 * Copyright (c) Teledyne Marine 2021. All rights reserved.
 *
 */

#include "PDD_Include.h"
#include <conio.h>
#include <iostream>
#include <math.h>
#include <sstream>

/** @brief Main program
*/
int main()
{
    // Invalid data will be marked as INFINITY
    tdym::PDD_SetInvalidValue(INFINITY);

    // Open PD0 file
    FILE* fp;
    char filename[] = "C:/RDI_DATA/my_file.pd0";
    int err = fopen_s(&fp, filename, "rb");

    if (fp == nullptr || err != 0)
    {
        // File failed to open
        std::cout << "Failed to open " << filename << std::endl;
        std::cout << "Copy file to that directory or change filename in the code" << std::endl;
        std::cout << "Press any key to continue" << std::endl;
    }
    else
    {
        // Create and initialize decoder
        tdym::PDD_Decoder* decoder = new tdym::PDD_Decoder();
        tdym::PDD_InitializeDecoder(decoder);

        // Create ensemble
        tdym::PDD_PD0Ensemble ens;

        // Initialize input buffer
        unsigned char* buff = new unsigned char[10000];

        // Check file size
        _fseeki64(fp, 0, SEEK_END);
        long long fileSize = _ftelli64(fp);
        _fseeki64(fp, 0, SEEK_SET);

        // Percentage of file processed
        int perc = 0;

        if (fileSize > 0)
        {
            unsigned int num = 0;
            int read = 0;
            bool foundAny = false;
            std::string str;
            do
            {
                // Read some data
                read = (int)fread(buff, 1, 10000, fp);
                if (read > 0)
                {
                    // Add data to decoder
                    tdym::PDD_AddDecoderData(decoder, buff, read);
                    int found = 0;
                    do
                    {
                        // Decode ensembles from decoder
                        found = tdym::PDD_GetPD0Ensemble(decoder, &ens);
                        if (found)
                        {
                            // Note: You can access ensemble structure directly but below helper functions can be useful
                            
                            // Get ensemble number
                            num = tdym::PDD_GetEnsembleNumber(&ens, tdym::PDBB);

                            // Get ADCP information
                            tdym::PDD_ADCPInfo info;
                            tdym::PDD_GetADCPInfo(&ens, &info);

                            // Get sensors
                            tdym::PDD_Sensors sensors;
                            tdym::PDD_GetSensors(&ens, &sensors, tdym::PDBB);

                            // Get heading, pitch, roll sensor
                            tdym::PDD_HPRSensor hpr;
                            tdym::PDD_GetHPRSensor(&ens, &hpr, tdym::PDBB);

                            // Get vessel velocities in m/s
                            double array[FOUR_BEAMS];
                            tdym::PDD_GetVesselVelocities(&ens, array);
                            std::stringstream ss;
                            ss << ", Vessel velocities (m/s): ";
                            for (int i = 0; i < 3; i++)
                            {
                                ss << " " << array[i];
                            }

                            // Get range to bottom in meters
                            double range = tdym::PDD_GetRangeToBottom(&ens, array);
                            ss << ", Range (m): " << range;
                            str = ss.str();

                            // Get profile ping setup
                            tdym::PDD_PingSetup setup;
                            tdym::PDD_GetPingSetup(&ens, &setup, tdym::PDBB);

                            // Get water profile velocities
                            if (setup.cellCount > 0 && setup.pingCount > 0)
                            {
                                int size = FOUR_BEAMS * setup.cellCount;
                                double* wpVel = new double[(size_t)size];
                                tdym::PDD_GetProfileVelocities(&ens, wpVel, size, tdym::PDBB);
                                delete[] wpVel;
                            }

                            foundAny = true;
                        }
                    } while (found > 0);

                    // Calculate percentage of file that was processed
                    long long pos = _ftelli64(fp);
                    perc = (int)((pos * 100) / fileSize);

                    if (foundAny)
                    {
                        // Display last ensemble progress
                        std::cout << "Ensemble " << num << str << ", File: " << perc << " %               \r";
                    }
                    else
                    {
                        // No ensembles found
                        std::cout <<  perc << " %               \r";
                    }
                }

            } while (read > 0);
        }

        fclose(fp);
        std::cout << "\nFinished reading file.  Press any key to continue.\n";

        // Cleanup resources
        delete[] buff;
        buff = nullptr;

        delete decoder;
        decoder = nullptr;
    }

    // Press any key to continue
    int key = _getch();
    key;
}
