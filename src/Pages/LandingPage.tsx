import { Box, Stack } from '@mui/material'
import { ReactSVG } from 'react-svg'
import { LayoutContainer, PageLayout } from '../Layouts'
import { ButtonLink } from '../components/Link'
import edgeImage from '../images/edge.svg'
import title from '../images/title.svg'

// Needs more work to be pretty on small screen sizes
export const LandingPage = () => {
  return (
    <PageLayout
      contained={false}
      sx={{ backgroundColor: theme => theme.palette.primary.dark, flexGrow: 1 }}
    >
      <Box component="article" sx={{ position: 'relative' }}>
        <Box
          sx={{
            position: 'absolute',
            backgroundColor: 'white',
            width: '45%',
            height: '100%',
            right: 0,
          }}
        >
          <img
            src={edgeImage}
            style={{
              height: '100%',
              transform: 'translateX(-100%) scale(-1, -1)',
              position: 'absolute',
              left: 0,
              top: 0,
            }}
          />
        </Box>

        <LayoutContainer
          sx={{
            position: 'relative',
            zIndex: '1',
            display: 'flex',
            color: 'white',
            backgroundColor: 'transparent',
          }}
        >
          <Stack maxWidth="500px" marginY={6}>
            <Box component="h1" sx={{ maxWidth: '250px' }}>
              <ReactSVG
                src={title}
                style={{ fill: 'white', height: '100%' }}
                title="Fair Slice"
              />
            </Box>

            <Box sx={{ fontSize: '24px' }}>
              <p>Sharing is Caring.</p>
              <p>Learn the science of provably fair resource splitting.</p>
            </Box>

            <Stack direction="row" alignItems="center" spacing={2}>
              <ButtonLink variant="outlined" color="inherit" href={'/graph'}>
                Splitting Tool
              </ButtonLink>

              <ButtonLink variant="contained" href={'/learn'}>
                Learn
              </ButtonLink>
            </Stack>
          </Stack>

          <Stack
            sx={{
              margin: 6,
              marginLeft: {
                xs: 4,
                sm: 20,
              },
            }}
            alignItems="center"
            justifyContent="center"
            direction="column"
          >
            <img
              src="https://creazilla-store.fra1.digitaloceanspaces.com/emojis/53176/birthday-cake-emoji-clipart-md.png"
              style={{ width: '100%', maxWidth: 500 }}
              alt=""
            />
            <div
              style={{
                position: 'relative',
                top: '-200px',
                textAlign: 'center',
                fontSize: 40,
              }}
            >
              PLACEHOLDER
            </div>
          </Stack>
        </LayoutContainer>
      </Box>
    </PageLayout>
  )
}
