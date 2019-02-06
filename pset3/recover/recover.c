#include <stdio.h>
#include <stdlib.h>
#include <cs50.h>

#define BlockSize 512

int main(int argc, char *argv[])
{
    //Make sure that I have one command line argument
    if (argc != 2)
    {
        fprintf(stderr, "Please enter file to open.\n");
        return 1;
    }

    //Open the file entered into the command line
    FILE *file = fopen(argv[1], "r");

    //If the file does not exist, throw an error
    if (file == NULL)
    {
        fprintf(stderr, "Could not open %s.\n", argv[1]);
        return 2;
    }

    // create buffer for reading flie
    unsigned char buffer[BlockSize];

    // flag to check if it is a new JPEG
    bool foundJPEG = false;

    // char array to store the resultant string (3+1+3+1) ,file pointer to store new image and counter to record each file
    char filename[8];
    FILE *img = NULL;
    int counter = 0;

    while (fread(buffer, BlockSize, 1, file) && !feof(file))
    {
        // check if it is the start of a new JPEG
        if (buffer[0] == 0xff && buffer[1] == 0xd8 && buffer[2] == 0xff && (buffer[3] & 0xf0) == 0xe0)
        {
            // close the current jpeg file to start a new one
            if (foundJPEG)
            {
                fclose(img);
            }
            foundJPEG = true;
            // make a new JPEG
            sprintf(filename, "%03i.jpg", counter);
            img = fopen(filename, "w");
            counter ++;
        }

        // check if already found a JPEG
        if (foundJPEG)
        {
            fwrite(&buffer, BlockSize, 1, img);
        }

    }

    //close file and img
    fclose(file);
    fclose(img);

    // success
    return 0;



}
